import { api } from './api';
import type { FileNode } from '../types/api';

export async function listFiles(path: string): Promise<FileNode> {
    const res = await api.get<FileNode>('/list-files', { params: { path } });
    return res.data;
}

/** Abre o seletor nativo de pastas no back. Devolve '' se o usuário cancelar. */
export async function browseFolder(): Promise<string> {
    const res = await api.get<{ path: string }>('/browse-folder');
    return res.data.path;
}

export async function moveFile(sourcePath: string, destinationFolder: string): Promise<void> {
    await api.post('/move-file', {
        source_path: sourcePath,
        destination_folder: destinationFolder,
    });
}

export async function reorderFiles(folderPath: string, orderedPaths: string[]): Promise<void> {
    await api.post('/reorder-files', {
        folder_path: folderPath,
        ordered_paths: orderedPaths,
    });
}
