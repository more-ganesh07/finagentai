// API service for KiteInfi backend integration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Market Chatbot - Synchronous endpoint
 * @param {string} userQuery - The user's query
 * @returns {Promise<{response: string}>}
 */
export async function marketChatbotSync(userQuery) {
    try {
        const response = await fetch(`${API_BASE_URL}/market_chatbot/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: userQuery }),
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
            } catch (e) {
                // Ignore error reading body
            }
            throw new Error(
                `Server error ${response.status}${errorBody ? `: ${errorBody}` : ''}`
            );
        }

        const data = await response.json();

        // Validate response structure
        if (!data || typeof data.response !== 'string') {
            throw new Error('Invalid response format from server');
        }

        return data;
    } catch (error) {
        console.error('Market chatbot sync error:', error);
        throw error;
    }
}

/**
 * Portfolio Chatbot - Synchronous endpoint
 * @param {string} userQuery - The user's query
 * @returns {Promise<{response: string}>}
 */
export async function portfolioChatbotSync(userQuery) {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/chatbot_sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: userQuery }),
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
            } catch (e) {
                // Ignore error reading body
            }
            throw new Error(
                `Server error ${response.status}${errorBody ? `: ${errorBody}` : ''}`
            );
        }

        const data = await response.json();

        // Validate response structure
        if (!data || typeof data.response !== 'string') {
            throw new Error('Invalid response format from server');
        }

        return data;
    } catch (error) {
        console.error('Portfolio chatbot sync error:', error);
        throw error;
    }
}

/**
 * Market Chatbot Stream - Initialize streaming connection
 * @param {string} userQuery - The user's query
 * @param {Function} onChunk - Callback function for each chunk of data
 * @param {Function} onComplete - Callback function when stream completes
 * @param {Function} onError - Callback function for errors
 * @param {AbortSignal} signal - Signal to abort request
 */
export async function marketChatbotStream(userQuery, onChunk, onComplete, onError, signal) {
    try {
        const response = await fetch(`${API_BASE_URL}/market_chatbot/stream`, {
            method: 'POST',
            signal,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: userQuery }),
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
            } catch (e) {
                // Ignore error reading body
            }
            throw new Error(
                `Server error ${response.status}${errorBody ? `: ${errorBody}` : ''}`
            );
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (onComplete) onComplete();
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.error) {
                            if (onError) onError(new Error(data.error));
                            return;
                        }
                        if (data.done) {
                            if (onComplete) onComplete();
                            return;
                        }
                        if ((data.type === 'content' || !data.type) && data.content && onChunk) {
                            onChunk(data.content);
                        }
                        // Handle status updates if needed (could be passed to a separate callback later)
                        if (data.type === 'status') {
                            console.log('Status update:', data.content);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Market chatbot stream error:', error);
        if (onError) onError(error);
        throw error;
    }
}

/**
 * Portfolio Chatbot Stream - Initialize streaming connection (triggers Kite login)
 * @param {string} userQuery - The user's query
 * @param {Function} onChunk - Callback function for each chunk of data
 * @param {Function} onComplete - Callback function when stream completes
 * @param {Function} onError - Callback function for errors
 */
export async function portfolioChatbotStream(userQuery, onChunk, onComplete, onError, signal) {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/chatbot_stream`, {
            method: 'POST',
            signal,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: userQuery }),
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
            } catch (e) {
                // Ignore error reading body
            }
            throw new Error(
                `Server error ${response.status}${errorBody ? `: ${errorBody}` : ''}`
            );
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (onComplete) onComplete();
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.error) {
                            if (onError) onError(new Error(data.error));
                            return;
                        }
                        if (data.done) {
                            if (onComplete) onComplete();
                            return;
                        }
                        if (data.content && onChunk) {
                            onChunk(data.content);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Portfolio chatbot stream error:', error);
        if (onError) onError(error);
        throw error;
    }
}

/**
 * Portfolio Report - Generate and email portfolio report
 * @returns {Promise<{status: string, message: string}>}
 */
export async function generatePortfolioReport() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/report/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
            } catch (e) {
                // Ignore error reading body
            }
            throw new Error(
                `Server error ${response.status}${errorBody ? `: ${errorBody}` : ''}`
            );
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Portfolio report error:', error);
        throw error;
    }
}

/**
 * Portfolio Status - Check if Kite session is active
 * @returns {Promise<{connected: boolean}>}
 */
export async function getPortfolioStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/status`);
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Portfolio status error:', error);
        throw error;
    }
}

/**
 * Portfolio Connect URL - Get the Zerodha login URL
 * @returns {Promise<{login_url: string}>}
 */
export async function getPortfolioConnectUrl() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/connect`);
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Portfolio connect URL error:', error);
        throw error;
    }
}

/**
 * Portfolio Disconnect - Wipe Zerodha session
 * @returns {Promise<{status: string, message: string}>}
 */
export async function disconnectPortfolio() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/disconnect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Portfolio disconnect error:', error);
        throw error;
    }
}

/**
 * Portfolio Report HTML - Fetch the last generated report content
 * @returns {Promise<string>} - HTML content
 */
export async function getPortfolioReportHTML() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/report/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        const data = await response.json();
        return data.html || "";
    } catch (error) {
        console.error('Portfolio report fetch error:', error);
        throw error;
    }
}

/**
 * Portfolio Report Demo - Fetch the pre-generated demo report content
 * @returns {Promise<string>} - HTML content
 */
export async function getPortfolioReportDemo() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/report/demo`);
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        const data = await response.json();
        return data.html || "";
    } catch (error) {
        console.error('Portfolio report demo fetch error:', error);
        throw error;
    }
}

/**
 * Portfolio Report Email - Send the report to the user's email
 * Note: Requires backend implementation of POST /portfolio/report/send-email
 * @returns {Promise<{status: string, message: string}>}
 */
export async function sendPortfolioReportEmail() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/report/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Portfolio report email error:', error);
        throw error;
    }
}

/**
 * STT Service - Start voice transcription
 * @returns {Promise<{status: string, message: string}>}
 */
export async function sttStart() {
    try {
        const response = await fetch(`${API_BASE_URL}/stt/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Server error ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('STT Start error:', error);
        throw error;
    }
}

/**
 * STT Service - Stop voice transcription
 * @returns {Promise<{status: string, message: string}>}
 */
export async function sttStop() {
    try {
        const response = await fetch(`${API_BASE_URL}/stt/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Server error ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('STT Stop error:', error);
        throw error;
    }
}

/**
 * STT Service - WebSocket instance
 * @returns {WebSocket}
 */
export function sttWebSocket() {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/stt/ws';
    return new WebSocket(wsUrl);
}

export async function sttStream(onTranscript, signal) {
    try {
        const response = await fetch(`${API_BASE_URL}/stt/stream`, {
            method: 'GET',
            signal,
            headers: {
                'Cache-Control': 'no-cache',
            },
        });

        if (!response.ok) {
            throw new Error(`Server error ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        // The backend returns { text: "...", is_final: boolean }
                        if (data && data.text && onTranscript) {
                            onTranscript(data);
                        }
                    } catch (e) {
                        console.error('Error parsing transcript data:', e);
                    }
                }
            }
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('STT stream error:', error);
            throw error;
        }
    }
}

/**
 * Stock Buddy - Get stock information
 * @param {string} query - The stock query
 * @returns {Promise<Object>} - Stock information response
 */
export async function getStockBuddy(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/stock_buddy/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_query: query }),
        });

        if (!response.ok) {
            let errorBody = '';
            try {
                errorBody = await response.text();
                // Try to parse as JSON to extract "detail"
                const parsed = JSON.parse(errorBody);
                if (parsed.detail) {
                    errorBody = parsed.detail;
                }
            } catch (e) {
                // Not JSON or no detail, keep original errorBody or status
            }
            throw new Error(errorBody || `Server error ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Stock buddy error:', error);
        throw error;
    }
}

/**
 * Market Indices - Static one-time fetch
 * @returns {Promise<Object>} - Market indices data
 */
export async function getMarketIndices() {
    try {
        const response = await fetch(`${API_BASE_URL}/market_indices`);
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Market indices fetch error:', error);
        throw error;
    }
}

/**
 * Market Indices - Stream live updates
 * @param {Function} onData - Callback for new data
 * @returns {AbortController} - Controller to stop the stream
 */
export function marketIndicesStream(onData) {
    const controller = new AbortController();
    const url = `${API_BASE_URL}/market_indices/stream`;

    // We use a manual fetch + reader here because EventSource doesn't support headers/POST (if needed) 
    // and standard fetch allows easier integration with our existing logic.
    // However, since it's a simple GET SSE, we can use EventSource if preferred.
    // Given the backend implementation, a standard EventSource is easiest.

    const es = new EventSource(url);

    es.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onData(data);
        } catch (e) {
            console.error('Error parsing market index stream data', e);
        }
    };

    es.onerror = (err) => {
        console.error('Market index stream error', err);
        es.close();
    };

    return {
        abort: () => es.close()
    };
}


