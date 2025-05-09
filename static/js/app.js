let imagenBlob = null;
const btnProcesar = document.querySelector("button[onclick='enviarImagen()']");

document.getElementById("imagen").addEventListener("change", () => {
  const file = document.getElementById("imagen").files[0];
  if (file) {
    const preview = document.getElementById("preview");
    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";
    imagenBlob = file;
    btnProcesar.disabled = false;
    document.getElementById("resultado").style.display = "none";
    document.getElementById("mensaje-db").style.display = "none";
  }
});

function abrirCamara() {
  const video = document.getElementById("video");
  const btnCapturar = document.getElementById("btnCapturar");

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
      video.style.display = "block";
      btnCapturar.style.display = "inline-block";
      btnProcesar.disabled = true;
    })
    .catch(err => {
      alert("No se pudo acceder a la cámara: " + err.message);
    });
}

function capturarFoto() {
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const preview = document.getElementById("preview");

  const width = video.videoWidth;
  const height = video.videoHeight;
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, width, height);

  const stream = video.srcObject;
  stream.getTracks().forEach(track => track.stop());
  video.style.display = "none";
  document.getElementById("btnCapturar").style.display = "none";

  const dataURL = canvas.toDataURL("image/jpeg");
  preview.src = dataURL;
  preview.style.display = "block";

  canvas.toBlob(blob => {
    imagenBlob = blob;
    btnProcesar.disabled = false;
  }, "image/jpeg");
}

async function enviarImagen() {
  if (!imagenBlob) {
    alert("Por favor selecciona o captura una imagen.");
    return;
  }

  const formData = new FormData();
  formData.append("file", imagenBlob, "imagen.jpg");

  try {
    const response = await fetch("/detectar", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Error desconocido");
    }

    const data = await response.json();
    document.getElementById("num").innerText = data.numero;
    document.getElementById("palabras").innerText = data.palabras;
    document.getElementById("factorial").innerText = data.factorial;
    document.getElementById("resultado").style.display = "block";

    const mensajeDB = document.getElementById("mensaje-db");
    if (data.mensaje_db) {
      mensajeDB.textContent = data.mensaje_db;
      mensajeDB.style.display = "block";
      mensajeDB.style.color = data.mensaje_db.includes("✅") ? "green" : "red";
    }

  } catch (err) {
    alert("❌ Error al procesar la imagen:\n" + err.message);
  }
}
