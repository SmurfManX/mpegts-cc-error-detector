document.addEventListener('DOMContentLoaded', function() {
    const activeChannels = {}; // Keep track of active channels for graph updates
    const updateInterval = 1000; // Update interval for graph data in milliseconds

function startUpdatingGraph(channelIndex, channelName) {
    const ctx = document.getElementById(`chart_${channelIndex}`).getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Packet Loss (%)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                data: [],
                fill: false,
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                annotation: {
                    annotations: [],
                },
            },
        }
    });

    const fetchData = () => {
        fetch(`/data/${channelName}`)
            .then(response => response.json())
            .then(packet_losses => {
                const now = new Date();
                const formattedTime = now.toLocaleTimeString();
                chart.data.labels.push(formattedTime);
                while (chart.data.labels.length > packet_losses.length) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                chart.data.datasets[0].data = packet_losses;
                chart.update(); // Update the chart with new data
                
                const latestData = packet_losses[packet_losses.length - 1];
                
                chart.options.scales.y.suggestedMin = Math.max(0, latestData - 10);
                chart.options.scales.y.suggestedMax = Math.min(100, latestData + 10);
                
                const annotation = {
                    type: 'line',
                    mode: 'vertical',
                    scaleID: 'x',
                    value: formattedTime,
                    borderColor: 'rgba(0, 255, 0, 0.5)',
                    borderWidth: 2,
                    label: {
                        enabled: true,
                        content: 'Latest Log: ' + formattedTime,
                        position: 'top',
                        backgroundColor: 'rgba(0, 255, 0, 0.5)'
                    }
                };
                chart.options.plugins.annotation.annotations = [annotation];
            });
    };

    fetchData();
    setInterval(fetchData, 1000); // Fetch data every 1 seconds
}


    // Move toggleGraph function here
    function toggleGraph(channelIndex) {
        const container = document.getElementById(`graphContainer_${channelIndex}`);
        const channelName = document.getElementById(`channelName_${channelIndex}`).textContent;

        if (container.style.display === "none") {
            container.style.display = "block";
            startUpdatingGraph(channelIndex, channelName);
        } else {
            container.style.display = "none";
            clearInterval(activeChannels[channelName]);
        }
    }

    // Attach the toggleGraph function to the button click event
    const toggleButtons = document.querySelectorAll('.toggle-graph-button');
    toggleButtons.forEach((button, index) => {
        button.addEventListener('click', () => toggleGraph(index));
    });
});
