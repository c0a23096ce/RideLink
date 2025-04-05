// lib/apiClient.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // FastAPIのURL
  withCredentials: true,
});

export default apiClient;
