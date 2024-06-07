const fetchData = () => {
    return $.get("http://localhost:8081/api/data");
}

let times = [];
let temperatures = [];

const updateGraph = (newData) => {
    times.push(newData.time);
    temperatures.push(newData.temperature);
    
    if(times.length > 10) { 
        times.shift();
        temperatures.shift();
    }

    Plotly.newPlot('chart', [{
        x: times,
        y: temperatures,
        type: 'scatter'
    }], {
        title: 'Temperature over Time'
    });
}

document.getElementById("toggleThemeButton").addEventListener("click", function() {
    document.body.classList.toggle('dark-mode');
});

$(document).ready(function(){
    $('#helpBtn').on('click', function(){
        $('#contactInfo').toggle();
    });
});

const updateInfoBar = (data) => {
    $('#currentTemp').text(parseFloat(data.temperature).toFixed(2));
    $('#status').text(data.status);
    $('#fanStatus').text(data.fan_status); 
    $('#doorStatus').text(data.door_open ? "Open" : "Closed"); 
    $('#currentTime').text(data.time || "N/A");
    $('#currentDate').text(data.date || "N/A");
}

const showModal = (modalId) => {
    const modal = document.getElementById(modalId);
    modal.style.display = "block";

    const closeButton = modal.querySelector(".close-btn");
    closeButton.onclick = () => {
        modal.style.display = "none";
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }
}

const runUpdates = () => {
    fetchData().done(data => {
        updateInfoBar(data);
        updateGraph(data);
        console.log(data);
    });
}

setInterval(runUpdates, 1000);

document.getElementById("homeButton").addEventListener("click", function () {
    location.reload();
});

document.getElementById("aboutButton").addEventListener("click", function () {
    showModal("aboutModal");
});

document.getElementById("contactButton").addEventListener("click", function () {
    showModal("contactModal");
});
