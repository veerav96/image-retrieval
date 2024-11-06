document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
});

function initializeElements() {
    window.fileInput = document.getElementById('fileInput');
    window.uploadBtn = document.getElementById('uploadBtn');
    window.canvasContainer = document.getElementById('canvasContainer');
    window.canvas = document.getElementById('imageCanvas');
    window.ctx = canvas.getContext('2d');
    window.submitBtn = document.getElementById('submitBtn');
    window.redoBtn = document.getElementById('redoBtn');
    window.pointsInput = document.getElementById('pointsInput');
    window.statusElement = document.getElementById('status');
    window.form = document.getElementById('uploadForm');
    window.fileLabel = document.querySelector('.file-label');
    window.canvasTitle = document.getElementById('canvasTitle');
    window.tooltip = document.getElementById('tooltip');
    window.goBackBtn = document.getElementById('goBackBtn');

    window.image = new Image();
    window.points = [];

    window.MAX_WIDTH = 600;
    window.MAX_HEIGHT = 400;

    window.imageWidth = 0;
    window.imageHeight = 0;
    window.scaleX = 0;
    window.scaleY = 0;
    window.offsetX = 0;
    window.offsetY = 0;
}

function initializeEventListeners() {
    setupFileInputListener();
    setupUploadButtonListener();
    setupCanvasClickListener();
    setupRedoButtonListener();
    setupSubmitButtonListener();
    setupMouseMoveListener();
    setupGoBackButtonListener();
}

function setupFileInputListener() {
    fileInput.addEventListener('change', handleFileInputChange);
}

function setupUploadButtonListener() {
    uploadBtn.addEventListener('click', handleUploadButtonClick);
}

function setupCanvasClickListener() {
    canvas.addEventListener('click', handleCanvasClick);
}

function setupRedoButtonListener() {
    redoBtn.addEventListener('click', handleRedoButtonClick);
}

function setupSubmitButtonListener() {
    form.addEventListener('submit', handleSubmit);
}

function setupMouseMoveListener() {
    canvas.addEventListener('mousemove', handleCanvasMouseMove);
    canvas.addEventListener('mouseleave', handleCanvasMouseLeave);
}

function setupGoBackButtonListener() {
    goBackBtn.addEventListener('click', handleGoBackButtonClick);
}

// Event Handlers

function handleFileInputChange() {
    if (fileInput.files.length > 0) {
        uploadBtn.disabled = false;
        //fileLabel.textContent = fileInput.files[0].name;
    } else {
        uploadBtn.disabled = true;
        fileLabel.textContent = 'Choose File';
    }
}

function handleUploadButtonClick() {
    if (fileInput.files.length === 0) {
        alert('Please select an image file.');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = function (e) {
        image.onload = () => {
            imageWidth = image.width;
            imageHeight = image.height;

            // Calculate scale factor and set canvas dimensions
            const scaleFactor = Math.min(MAX_WIDTH / imageWidth, MAX_HEIGHT / imageHeight);
            canvas.width = imageWidth * scaleFactor;
            canvas.height = imageHeight * scaleFactor +50; // Add extra space for padding
            scaleX = scaleFactor;
            scaleY = scaleFactor;

            // Calculate offsets to center image
            offsetX = (canvas.width - imageWidth * scaleFactor) / 2;
            offsetY = (canvas.height - imageHeight * scaleFactor) / 2 +50; // Add extra space for padding

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(image, offsetX, offsetY, imageWidth * scaleFactor, imageHeight * scaleFactor);

            canvasContainer.style.display = 'block';
            toggleUploadSectionVisibility(false);
            submitBtn.style.display = 'none';
            redoBtn.style.display = 'inline-block';
            canvasTitle.style.display = 'block';
        };
        image.src = e.target.result;
    };
    reader.onerror = () => {
        alert('Error reading file.');
    };
    reader.readAsDataURL(file);
}

function handleCanvasClick(e) {
    if (points.length < 4) {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        const imageCoords = canvasToImageCoordinates(canvasX, canvasY);
        if (imageCoords.x >= 0 && imageCoords.y >= 0 && imageCoords.x <= imageWidth && imageCoords.y <= imageHeight){
            points.push(imageCoords);
            if (points.length === 4) {
                points = sortPoints(points);
                drawQuadrilateral();
                pointsInput.value = JSON.stringify(points);
                submitBtn.style.display = 'inline-block';
            } else {
                drawPoints();
            }
        }
    }
}

function handleRedoButtonClick() {
    points = [];
    pointsInput.value = '';
    drawPoints();
    submitBtn.style.display = 'none';
    // Clear task status and result
    statusElement.textContent = '';
    const resultContainer = document.getElementById('resultContainer');
    const resultElement = document.getElementById('result');
    // Hide and clear the result container
    resultContainer.style.display = 'none';
    resultElement.innerHTML = '';  // Clear any displayed URLs
}

function handleSubmit(e) {
    e.preventDefault();
    // Clear any previous results
    const resultContainer = document.getElementById('resultContainer');
    const resultElement = document.getElementById('result');
    const statusElement = document.getElementById('status');

    resultElement.innerHTML = '';  // Clear previous results
    resultContainer.style.display = 'none';  // Hide the result container initially
    statusElement.textContent = '';  // Clear the status message

    const formData = new FormData();
    const file = fileInput.files[0];

    if (!file) {
        console.error('No file selected.');
        return;
    }

    try {
        const coordinates = JSON.parse(pointsInput.value);
        const coordinateTuples = coordinates.map(coord => [coord.x, coord.y]);

        // Append coordinates as a JSON string
        formData.append('coordinates', JSON.stringify(coordinateTuples));

        // Append the image file
        formData.append('image', file);

        fetch('/papyrus/submit/', { method: 'POST', body: formData })
            .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok'))
            .then(data => {
                statusElement.textContent = 'Task Status: ' + data.status;
                if (data.task_id) pollTaskStatus(data.task_id);
            })
            .catch(error => statusElement.textContent = 'Error: ' + error.message);
    } catch (error) {
        console.error('Invalid JSON format for coordinates:', pointsInput.value);
    }
}



function handleCanvasMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    const imageCoords = canvasToImageCoordinates(canvasX, canvasY);

    tooltip.style.left = `${e.pageX + 10}px`;
    tooltip.style.top = `${e.pageY + 10}px`;
    tooltip.textContent = `x: ${Math.round(imageCoords.x)}, y: ${Math.round(imageCoords.y)}`;
    tooltip.style.display = 'block';
}

function handleCanvasMouseLeave() {
    tooltip.style.display = 'none';
}

function handleGoBackButtonClick() {
    canvasContainer.style.display = 'none';
    submitBtn.style.display = 'none';
    redoBtn.style.display = 'none';
    points = [];
    pointsInput.value = '';
    toggleUploadSectionVisibility(true);
    fileInput.value = '';
    uploadBtn.disabled = true;
    // Clear task status and result
    statusElement.textContent = '';
    const resultContainer = document.getElementById('resultContainer');
    const resultElement = document.getElementById('result');
    // Hide and clear the result container
    resultContainer.style.display = 'none';
    resultElement.innerHTML = '';  // Clear any displayed URLs
}

// Utility Functions

function toggleUploadSectionVisibility(shouldShow) {
    if (shouldShow) {
        fileInput.style.display = 'block';
        uploadBtn.style.display = 'block';
    } else {
        fileInput.style.display = 'none';
        uploadBtn.style.display = 'none';
    }
}

function canvasToImageCoordinates(canvasX, canvasY) {
    const imageX = (canvasX - offsetX) / scaleX;
    const imageY = (canvasY - offsetY) / scaleY;
    return { x: imageX, y: imageY };
}

function drawPoints() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, offsetX, offsetY, imageWidth * scaleX, imageHeight * scaleY);
    ctx.fillStyle = 'red';
    points.forEach(point => {
        const canvasX = point.x * scaleX + offsetX;
        const canvasY = point.y * scaleY + offsetY;
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 3, 0, Math.PI * 2);
        ctx.fill();
    });
}

function drawQuadrilateral() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, offsetX, offsetY, imageWidth * scaleX, imageHeight * scaleY);
    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(points[0].x * scaleX + offsetX, points[0].y * scaleY + offsetY);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x * scaleX + offsetX, points[i].y * scaleY + offsetY);
    }
    ctx.closePath();
    ctx.stroke();
}

function sortPoints(pts) {
    if (pts.length !== 4) return pts;

    const centroid = pts.reduce((acc, pt) => {
        acc.x += pt.x;
        acc.y += pt.y;
        return acc;
    }, { x: 0, y: 0 });

    centroid.x /= pts.length;
    centroid.y /= pts.length;

    pts.sort((a, b) => {
        const angleA = Math.atan2(a.y - centroid.y, a.x - centroid.x);
        const angleB = Math.atan2(b.y - centroid.y, b.x - centroid.x);
        return angleA - angleB;
    });

    return pts;
}

function pollTaskStatus(task_id) {
    const interval = setInterval(() => {
        fetch(`/papyrus/result/${task_id}`)  // Use backticks here for template literal
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Check the correct key for the status
                if (data.query_status === 'SUCCESS') {
                    clearInterval(interval);  // Stop polling when task completes
                    statusElement.textContent = 'Task completed successfully!';
                    console.log('Result:', data.query_result);  // Use the result here
                    // Display the URLs in the resultContainer as clickable links
                    const resultContainer = document.getElementById('resultContainer');
                    const resultElement = document.getElementById('result');
                    resultElement.innerHTML = '';  // Clear previous content

                    // Assuming data.query_result is an array of URLs
                    data.query_result.forEach(url => {
                        const linkElement = document.createElement('a');
                        linkElement.href = url;
                        linkElement.textContent = url;
                        linkElement.target = '_blank';  // Opens in a new tab
                        linkElement.style.display = 'block';  // Each URL on a new line
                        resultElement.appendChild(linkElement);
                    });

                    resultContainer.style.display = 'block';
                } else if (data.query_status === 'FAILURE') {
                    clearInterval(interval);  // Stop polling on failure
                    statusElement.textContent = 'Task failed.';
                } else {
                    // Task still in progress (PENDING, STARTED)
                    statusElement.textContent = 'Task Status: ' + data.query_status;
                }
            })
            .catch(error => {
                clearInterval(interval);  // Stop polling on error
                statusElement.textContent = 'Error: ' + error.message;
            });
    }, 2000);  // Poll every 2 seconds
}


