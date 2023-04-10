

function startAnimation() {
    var elements = document.querySelectorAll(".str");
    elements.forEach(function(element) {
      element.classList.add("animate");
      setTimeout(function() {
        element.classList.remove("animate");
      }, 3000);
    });
  }


function startAnimationbar() {
  var border = document.querySelector(".m");
  //border.querySelector(":after").style.animationPlayState = "running";
}

function saveAudio(blob, fileName) {
  const fileSaver = require('file-saver');
  fileSaver.saveAs(blob, fileName);
}

async function recordAudio() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  const audioChunks = [];

  // Add event listener for when data becomes available
  mediaRecorder.addEventListener("dataavailable", event => {
      audioChunks.push(event.data);
  });

  // Start recording
  mediaRecorder.start();

  // Wait for 3 seconds before stopping the recorder
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Stop the recorder
  mediaRecorder.stop();

  // Wait for the 'stop' event to fire before creating the Blob object
  await new Promise(resolve => mediaRecorder.addEventListener("stop", resolve));

  // Create a Blob object from the audio data
  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
  //console.log(audioBlob)
  // Return the Blob object
  sendAudio(audioBlob)
  // Simulate a mouse click:
      $.ajax({
        url: "/api",
        type: "GET",
        success: function(data) {
            if(data=='True'){
              window.location.href = '/results';
            }
        }
    });
}


function monitorVolume() {
  const mediaRecorder = new MediaRecorder(mediaStream);
  const audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(mediaStream);
  const processor = audioContext.createScriptProcessor(1024, 1, 1);
  let volume = 0;

  processor.onaudioprocess = function(event) {
    const buffer = event.inputBuffer.getChannelData(0);
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) {
      sum += buffer[i] * buffer[i];
    }
    volume = Math.sqrt(sum / buffer.length);
  };

  source.connect(processor);
  processor.connect(audioContext.destination);
  mediaRecorder.start();

  setInterval(() => {
    console.log(`Live volume: ${volume}`);
  }, 100);
}




function sendAudio(audioBlob) {
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/recording', true);
  xhr.setRequestHeader('Content-Type', 'application/octet-stream');
  xhr.onload = function() {
    if (xhr.status === 200) {
      //console.log('Audio sent successfully.');
    } else {
      console.error('Error sending audio:', xhr.statusText);
    }
  };
  xhr.onerror = function() {
    console.error('Error sending audio:', xhr.statusText);
  };
  xhr.send(audioBlob);
}
