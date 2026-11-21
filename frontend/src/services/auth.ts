import { api } from './api';
import type {
    CurrentUser,
    LoginPayload,
    LoginResponse,
    VerifyPayload,
    VerifyResponse,
} from '../types/api';

export async function requestLoginCode(payload: LoginPayload): Promise<LoginResponse> {
    const res = await api.post<LoginResponse>('/auth/login', payload);
    return res.data;
}

export async function verifyLoginCode(payload: VerifyPayload): Promise<VerifyResponse> {
    const res = await api.post<VerifyResponse>('/auth/verify', payload);
    return res.data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
    const res = await api.get<CurrentUser>('/user/me');
    return res.data;
}
