import axios from 'axios';

const API_BASE_URL = '/api'; // TODO: 실제 백엔드 주소로 변경 필요


const api = {
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append('image', file);
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
