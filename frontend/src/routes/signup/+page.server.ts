import type { UserCreate } from '$lib/interfaces/CreateModels.interface.js';
import { fail, redirect } from '@sveltejs/kit';

export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (token === undefined) return;
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch("http://localhost:8000/users/me", {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) return;

    throw redirect(302, "/chat")
}

export const actions = {
    create: async ({ cookies, request }) => {
        const data: FormData = await request.formData();
        const pw = data.get("password");
        const confirmPW = data.get("confPassword");
        if (pw !== confirmPW) return fail(422, {
            error: `Passwords do not match`
        });

        const sendData: UserCreate = {
            first_name: data.get("firstName"),
            last_name: data.get("lastName"),
            email: data.get("email"),
            target_language: data.get("language"),
            password: data.get("password")
        }

		try {
			const response: Response = await fetch('http://localhost:8000/users', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(sendData)
			});

			if (!response.ok) {
				const errorResponse = await response.json();
				console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
				throw new Error(`Error code: ${response.status}`);
			}

			const resData = await response.json();

			const userID: string = resData.id.toString();

            // TODO, need to add the JWT to cookie once logged in
            cookies.set('userID', userID, { path: "/" });
        } catch (error) {
            return fail(422, {
                error: error.message
            });
        }

        throw redirect(302, '/chat');
    }
}