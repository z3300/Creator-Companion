console.log('Script loaded');

function typeWriter(text, elem, i, callback) {
  if (i < text.length) {
    elem.append(text.charAt(i));
    setTimeout(function () {
      typeWriter(text, elem, i + 1, callback);
    }, 5);
  } else {
    if (typeof callback === 'function') {
      callback();
    }
  }
}

function getRandomExampleQuestion() {
  const randomIndex = Math.floor(Math.random() * questions.length);
  return questions[randomIndex];
}

$('#luckyButton').on('click', function (e) {
  e.preventDefault(); // Prevent form submission
  const randomQuestion = getRandomExampleQuestion();
  $('input[type="text"]').val(randomQuestion);
});

$(document).ready(function () {
  $('#queryForm').submit(function (e) {
    e.preventDefault();
    $('#response').text('');
    $('#spinner').show();
    $('.context-box').hide();

    const askButton = $('button[type="submit"]');
    askButton.prop('disabled', true);

    console.log('Submitting form');

    $.post('/api/creatorAI', $(this).serialize(), function (data) {
      console.log('Received data from server');
      console.log(data);

      $('#spinner').hide();
      for (var i = 0; i < data.titles.length; i++) {
        var title = data.titles[i];
        var context = data.contexts[i];
        var boxContent = '<span class="context-box-title">' + title + '</span><br>' + context;
        $('#context-box-' + (i + 1)).html(boxContent);

        $('#context-box-' + (i + 1)).delay(i * 200).fadeIn(800);
      }

      typeWriter(data.response, $('#response'), 0, function onAnimationComplete() {
        askButton.prop('disabled', false);
      });
    });
  });

  $('.example-question').on('click', function () {
    $('input[type="text"]').val($(this).text());
  });
});
