
// Simulate progress and lines (to be replaced with real-time updates via WebSocket or AJAX)
const progressBar = document.getElementById('progress-bar');
const progressLines = document.getElementById('progress-lines');
let progress = 0;
const lines = [
	'Extracting text from your resume...',
	'Analyzing sections and keywords...',
	'Checking ATS compatibility...',
	'Scoring clarity and impact...',
	'Finalizing analysis...'
];
let lineIdx = 0;

function updateProgress() {
	if (progress < 100) {
		progress += Math.floor(Math.random() * 10) + 5;
		if (progress > 100) progress = 100;
		progressBar.style.width = progress + '%';
		progressBar.textContent = progress + '%';
		if (progress > (lineIdx + 1) * 20 && lineIdx < lines.length) {
			progressLines.innerHTML += `<div>${lines[lineIdx]}</div>`;
			lineIdx++;
		}
		setTimeout(updateProgress, 600);
	} else {
		progressBar.style.width = '100%';
		progressBar.textContent = '100%';
		setTimeout(() => {
			window.location.href = window.analysisResultUrl;
		}, 800);
	}
}

if (progressBar && progressLines) {
	updateProgress();
}
