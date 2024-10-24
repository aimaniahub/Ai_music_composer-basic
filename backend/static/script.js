document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const musicPlayer = document.getElementById('musicPlayer');
    const audioPlayer = document.getElementById('audioPlayer');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    let currentMp3Filename = null;

    generateBtn.addEventListener('click', async function() {
        const genre = document.getElementById('genre').value;

        // Show loading indicator
        loadingIndicator.style.display = 'flex';
        musicPlayer.style.display = 'none';
        generateBtn.disabled = true;

        try {
            const response = await fetch('/generate_music', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    genre: genre
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update audio player with new music
            currentMp3Filename = data.mp3_filename;
            audioPlayer.src = `/download/${currentMp3Filename}`;
            await audioPlayer.load();

            // Show music player
            musicPlayer.style.display = 'block';
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;

        } catch (error) {
            alert('Error generating music: ' + error.message);
            loadingIndicator.style.display = 'none';
            generateBtn.disabled = false;
        }
    });

    downloadBtn.addEventListener('click', function() {
        if (currentMp3Filename) {
            const downloadLink = document.createElement('a');
            downloadLink.href = `/download/${currentMp3Filename}`;
            downloadLink.download = currentMp3Filename;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
    });
});
