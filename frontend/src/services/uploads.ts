import { api } from './api';
import type {
    ResumeUploadPayload,
    ResumeUploadResponse,
    StartUploadPayload,
    StartUploadResponse,
} from '../types/api';

/** Ids dos canais que ainda têm arquivos não enviados. */
export async function getPendingUploads(): Promise<string[]> {
    const res = await api.get<{ pending_channels?: string[] }>('/pending-uploads');
    return res.data?.pending_channels ?? [];
}

export async function startUpload(payload: StartUploadPayload): Promise<StartUploadResponse> {
    const res = await api.post<StartUploadResponse>('/start-upload', payload);
    return res.data;
}

export async function resumeUpload(payload: ResumeUploadPayload): Promise<ResumeUploadResponse> {
    const res = await api.post<ResumeUploadResponse>('/resume-upload', payload);
    return res.data;
}
