import serverSettings from '$lib/config/config.server.js';
import { error } from '@sveltejs/kit';

export async function load({ cookies, parent }) {
    const email = cookies.get("signupEmail");

    if (!email) {
        throw error(404, {
            message: `Not found.`
        });
    }

    await parent();

    const response = await fetch(`${serverSettings.apiBaseURL}/users/resend-verify-email?email=${email}`, {
        method: "GET"
    });

    if (!response.ok) {
        throw error(400, {
            message: `Failed to send an email. Please wait a bit and try again.`
        });
    }

    const success = await response.json();

    return {
        message: success.message
    }
}