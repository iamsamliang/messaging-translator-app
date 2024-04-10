import clientSettings from '$lib/config/config.client.js';
import { error } from '@sveltejs/kit';

export async function load({ url, fetch }) {
    const token = url.searchParams.get("token");

    if (!token) {
		error(404, {
        			message: 'Invalid Permissions.'
        		});
    }

    console.log(token);
    const response: Response = await fetch(`${clientSettings.apiBaseURL}/users/verify-account`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ verification_token: token })
    });
    console.log(response.status);

    if (!response.ok) {
        const errorResponse = await response.json();
        console.log(errorResponse);
        error(400, {
                    message: errorResponse.detail
                });
    }

    const success = await response.json();
    
    return {
        message: success.message
    }
}