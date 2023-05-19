import json
import pinecone
import openai
import os
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Firebase setup
cred = credentials.Certificate('firebasecreds.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize openai API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

embed_model = "text-embedding-ada-002"

index_name = 'colinsamir'

# Initialize connection to pinecone
pinecone.init(
    api_key= os.environ.get("PINECONE_API_KEY"),
    environment="eu-west1-gcp"
)
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        index_name,
        dimension=len(res['data'][0]['embedding']),
        metric='dotproduct'
    )

pinecone_index = pinecone.Index(index_name)

def creatorAI(query):
  res = openai.Embedding.create(
    input=[query],
    engine=embed_model
  ) 
  xq = res['data'][0]['embedding']
  search_results = pinecone_index.query(xq, top_k=7, include_metadata=True)

  contexts = [item['metadata']['text'] for item in search_results['matches']]
  titles = [item['metadata']['name'].replace('_', '') for item in search_results['matches']]

  formatted_results = [f"Episode Title: {title}\nContext: {context}" for title, context in zip(titles, contexts)]

  augmented_query = "\n\n---\n\n".join(formatted_results) + "\n\n-----\n\n" + query
  primer = f"""As the Creative Companion AI, answer the following question using the provided podcast segments from "The Colin and Samir Show," which discusses the creative economy and social media. You are required to mention the specific episode title you're referencing within your answer. If needed, use your prior knowledge to fill in any gaps. Keep your answer concise (no more than 6 sentences). If the question is inappropriate, simply respond with "I don't know". If the topics are not mentioned in the context respond with "I don't know." Do not add all the references at the end of the answer."""

  res = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[
          {"role": "system", "content": primer},
          {"role": "user", "content": augmented_query}
      ],
      temperature = .3
  )

  response_text = res['choices'][0]['message']['content']

  return titles, contexts, response_text

app = Flask(__name__)

def get_cached_question_answer(query):
    doc_ref = db.collection('questions_answers').document(query)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

def cache_question_answer(question, titles, contexts, response_text):
    doc_ref = db.collection('questions_answers').document(question)
    doc_ref.set({
        'datetime': datetime.now(),
        'question': question,
        'titles': titles,
        'contexts': contexts,
        'response_text': response_text
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/creatorAI', methods=['POST'])
def api_creatorAI():
    query = request.form['query']
    existing_question = get_cached_question_answer(query)

    if existing_question:
        titles, contexts, response_text = existing_question['titles'], existing_question['contexts'], existing_question['response_text']
    else:
        titles, contexts, response_text = creatorAI(query)
        cache_question_answer(query, titles, contexts, response_text)

    return jsonify(titles=titles, contexts=contexts, response=response_text)

if __name__ == '__main__':
    app.run(debug=True)


   
