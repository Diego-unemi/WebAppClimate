// scripts.js - Lógica AJAX y gráficos para el dashboard ESP32

// ========== UTILIDADES AJAX ========== //
async function fetchJSON(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error en la petición');
        return await response.json();
    } catch (e) {
        console.error('AJAX error:', e);
        return null;
    }
}

// ========== DASHBOARD PRINCIPAL ========== //
let chartTemp, chartHumidity, chartCO2;

async function updateDashboard() {
    const data = await fetchJSON('/api/data');
    if (!data) return;
    // Actualizar valores
    document.getElementById('temperatureValue').textContent = data.temperature ? data.temperature.toFixed(1) : '--';
    document.getElementById('humidityValue').textContent = data.humidity ? data.humidity.toFixed(1) : '--';
    document.getElementById('co2Value').textContent = data.co2_ppm ? Math.round(data.co2_ppm) : '--';
    document.getElementById('lastUpdate').textContent = data.timestamp || '--';
    updateStatus(data.status === 'connected');
    
    // Actualizar estados de los sensores
    updateSensorStatus('tempStatus', data.temperature, 'temp');
    updateSensorStatus('humStatus', data.humidity, 'hum');
    updateSensorStatus('co2Status', data.co2_ppm, 'co2');
}

function updateSensorStatus(elementId, value, sensorType) {
    const element = document.getElementById(elementId);
    if (!element || value === null || value === undefined) return;
    
    let status = 'Normal';
    let className = '';
    
    switch(sensorType) {
        case 'temp':
            if (value < 15) { status = 'Frío'; className = 'warning'; }
            else if (value > 30) { status = 'Caliente'; className = 'danger'; }
            else { status = 'Normal'; className = ''; }
            break;
        case 'hum':
            if (value < 30) { status = 'Seco'; className = 'warning'; }
            else if (value > 70) { status = 'Húmedo'; className = 'danger'; }
            else { status = 'Normal'; className = ''; }
            break;
        case 'co2':
            if (value > 2000) { status = 'Alto'; className = 'danger'; }
            else if (value > 1000) { status = 'Moderado'; className = 'warning'; }
            else { status = 'Normal'; className = ''; }
            break;
    }
    
    element.textContent = status;
    element.className = 'gauge-status ' + className;
}

function updateStatus(connected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Conectado';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Desconectado';
    }
}

// ========== GRÁFICAS INDIVIDUALES ========== //
async function updateHistoricalChart(hours = 24) {
    const data = await fetchJSON(`/api/historical?hours=${hours}`);
    if (!data) return;
    const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
    const temps = data.map(d => d.temperature);
    const hums = data.map(d => d.humidity);
    const co2s = data.map(d => d.co2_ppm);
    if (chartTemp) {
        chartTemp.data.labels = labels;
        chartTemp.data.datasets[0].data = temps;
        chartTemp.update('none');
    }
    if (chartHumidity) {
        chartHumidity.data.labels = labels;
        chartHumidity.data.datasets[0].data = hums;
        chartHumidity.update('none');
    }
    if (chartCO2) {
        chartCO2.data.labels = labels;
        chartCO2.data.datasets[0].data = co2s;
        chartCO2.update('none');
    }
}

// ========== INICIALIZACIÓN DE SENSORES ========== //
function initializeSensors() {
    // Los sensores se inicializan automáticamente con los valores por defecto
    updateSensorStatus('tempStatus', null, 'temp');
    updateSensorStatus('humStatus', null, 'hum');
    updateSensorStatus('co2Status', null, 'co2');
}

// ========== INICIALIZACIÓN ========== //
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar sensores
    initializeSensors();
    // Gráficas individuales
    if (window.Chart) {
        chartTemp = new Chart(document.getElementById('chartTemp').getContext('2d'), {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Temperatura (°C)', data: [], borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', tension: 0.4, fill: true, borderWidth: 2 }] },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { 
                    legend: { 
                        display: false 
                    } 
                }, 
                scales: { 
                    x: { 
                        ticks: { color: 'white', maxTicksLimit: 6, font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }, 
                    y: { 
                        ticks: { color: 'white', font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    } 
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 5
                    }
                }
            }
        });
        chartHumidity = new Chart(document.getElementById('chartHumidity').getContext('2d'), {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Humedad (%)', data: [], borderColor: '#4ecdc4', backgroundColor: 'rgba(78,205,196,0.1)', tension: 0.4, fill: true, borderWidth: 2 }] },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { 
                    legend: { 
                        display: false 
                    } 
                }, 
                scales: { 
                    x: { 
                        ticks: { color: 'white', maxTicksLimit: 6, font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }, 
                    y: { 
                        ticks: { color: 'white', font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    } 
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 5
                    }
                }
            }
        });
        chartCO2 = new Chart(document.getElementById('chartCO2').getContext('2d'), {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'CO2 (ppm)', data: [], borderColor: '#45b7d1', backgroundColor: 'rgba(69,183,209,0.1)', tension: 0.4, fill: true, borderWidth: 2 }] },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: { 
                    legend: { 
                        display: false 
                    } 
                }, 
                scales: { 
                    x: { 
                        ticks: { color: 'white', maxTicksLimit: 6, font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }, 
                    y: { 
                        ticks: { color: 'white', font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    } 
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 5
                    }
                }
            }
        });
    }
    // Actualizar datos periódicamente
    updateDashboard();
    updateHistoricalChart();
    setInterval(updateDashboard, 3000);
    setInterval(updateHistoricalChart, 30000);
});
