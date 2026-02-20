import axios from 'axios';

// Get the backend URL.
// If hosted locally, it will be http://localhost:8000
// If hosted elsewhere, it will use the current hostname and port 8000
const getBaseURL = () => {
    const { protocol, hostname } = window.location;
    // If we are on localhost, we might still want to point to 8000 explicitly
    // unless the production environment serves both from same port
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000/api';
    }
    return `${protocol}//${hostname}:8000/api`;
};

const api = axios.create({
    baseURL: getBaseURL(),
});

export default api;
