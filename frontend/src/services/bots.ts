import { api } from './api';
import type { BotInfo } from '../types/api';

export async function listBots(): Promise<BotInfo[]> {
    const res = await api.get<BotInfo[]>('/bots/infos');
    return res.data;
}

export async function addBot(token: string): Promise<void> {
    await api.post('/bots/add', { token });
}
