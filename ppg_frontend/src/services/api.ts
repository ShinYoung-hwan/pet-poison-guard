import axios from 'axios';


const API_BASE_URL = '/api';

const api = {
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file); // FastAPI expects 'file', in reality, it's image
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data; // { taskId: string }
    } catch (error) {
      throw error;
    }
  },
  getTaskStatus: async (taskId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/task/${taskId}`);
      return response.data; // { status: 'pending' | 'completed', data?: any }
    } catch (error) {
      throw error;
    }
  },
};

export default api;
