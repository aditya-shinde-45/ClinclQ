import { API_BASE_URL, getAuthHeaders } from './config';

export interface ApiError {
  detail: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      // Don't automatically logout - let the component handle it
      const error: ApiError = await response.json().catch(() => ({ detail: 'Authentication required. Please login again.' }));
      throw new Error(error.detail);
    }
    const error: ApiError = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail);
  }
  
  if (response.status === 204) {
    return {} as T;
  }
  
  return response.json();
}

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return handleResponse(response);
  },
  
  logout: async () => {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  }
};

// Patients API
export const patientsAPI = {
  search: async (query: string): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/patients/search?q=${encodeURIComponent(query)}`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  },
  
  getById: async (patientId: string): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/patients/${patientId}`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any>(response);
  },
  
  create: async (patientData: any): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/patients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(patientData)
    });
    return handleResponse<any>(response);
  },
  
  getTimeline: async (patientId: string): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/patients/${patientId}/timeline`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  },

  createTimelineEntry: async (patientId: string, data: any): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/patients/${patientId}/timeline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    });
    return handleResponse<any>(response);
  },

  getDoctors: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/patients/doctors`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  }
};

// Appointments API
export const appointmentsAPI = {
  getToday: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/appointments/today`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  },

  getUpcoming: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/appointments/upcoming`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  },

  getAll: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/appointments/all`, {
      headers: getAuthHeaders()
    });
    return handleResponse<any[]>(response);
  },
  
  createAppointment: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/appointments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    });
    return handleResponse(response);
  },
  
  updateStatus: async (appointmentId: number, status: string) => {
    const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ status })
    });
    return handleResponse(response);
  },

  update: async (appointmentId: number, data: { appointment_time: string; reason?: string }) => {
    const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    });
    return handleResponse(response);
  },

  delete: async (appointmentId: number) => {
    const response = await fetch(`${API_BASE_URL}/appointments/${appointmentId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  }
};

// Analyses API
export const analysesAPI = {
  request: async (data: any) => {
    const response = await fetch(`${API_BASE_URL}/analyses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data)
    });
    return handleResponse(response);
  },
  
  getById: async (analysisId: number) => {
    const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}`, {
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  },
  
  getByPatient: async (patientId: string) => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(`${API_BASE_URL}/analyses/patient/${patientId}`, {
        headers: getAuthHeaders(),
        signal: controller.signal
      });
      return handleResponse(response);
    } catch (error: any) {
      if (error?.name === "AbortError") {
        throw new Error("Loading saved reports timed out. Please try again.");
      }
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  },
  
  recordDecision: async (analysisId: number, decision: any) => {
    const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}/decision`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(decision)
    });
    return handleResponse(response);
  },

  triggerRagIndex: async (patientId?: string, forceReindex: boolean = false) => {
    const response = await fetch(`${API_BASE_URL}/analyses/rag/index`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ patient_id: patientId, force_reindex: forceReindex })
    });
    return handleResponse(response);
  },

  searchRag: async (patientId: string, query: string, topK: number = 4) => {
    const response = await fetch(`${API_BASE_URL}/analyses/rag/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ patient_id: patientId, query, top_k: topK })
    });
    return handleResponse(response);
  }
};

// Documents API
export const documentsAPI = {
  upload: async (patientId: string, category: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/documents/upload?patient_id=${patientId}&category=${category}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData
    });
    return handleResponse(response);
  },
  
  getByPatient: async (patientId: string) => {
    const response = await fetch(`${API_BASE_URL}/documents/patient/${patientId}`, {
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  }
};

// Admin API
export const adminAPI = {
  getUsers: async () => {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  },
  
  getMetrics: async () => {
    const response = await fetch(`${API_BASE_URL}/admin/metrics`, {
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  },
  
  getKnowledgeSources: async () => {
    const response = await fetch(`${API_BASE_URL}/admin/knowledge-sources`, {
      headers: getAuthHeaders()
    });
    return handleResponse(response);
  }
};
