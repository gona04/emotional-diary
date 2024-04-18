// audioService.js

export const uploadAudio = async (file:any) => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://127.0.0.1:8000/upload-audio/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload audio');
        }

        const data = await response.json();
        return data;
    } catch (error:any) {
        throw new Error('Error uploading audio: ' + error.message);
    }
};
