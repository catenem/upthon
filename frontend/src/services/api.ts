import axios from 'axios';

// Em desenvolvimento o padrão é o back local. Para outro endereço, defina
// REACT_APP_API_URL (ex.: "/api" para usar o proxy do setupProxy.js).
const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const api = axios.create({ baseURL });

/**
 * Mensagem de erro para mostrar ao usuário.
 *
 * O back sempre responde erros como `{"detail": "..."}` (ver app/core/errors.py),
 * por exemplo "Já existe um upload em andamento para este canal.". Usamos essa
 * mensagem quando existe e caímos em `fallback` só quando não há nada melhor.
 */
export function getErrorMessage(error: unknown, fallback: string): string {
    if (!axios.isAxiosError(error)) return fallback;

    if (!error.response) {
        return 'Não foi possível conectar ao back end. Ele está rodando?';
    }

    const detail = error.response.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;

    // Erros de validação do FastAPI (422) vêm como lista de { msg, loc, ... }
    if (Array.isArray(detail)) {
        const messages = detail
            .filter((d) => d?.msg)
            .map((d) => {
                const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : undefined;
                return field !== undefined ? `${field}: ${d.msg}` : String(d.msg);
            });
        if (messages.length > 0) return messages.join('; ');
    }

    return fallback;
}
