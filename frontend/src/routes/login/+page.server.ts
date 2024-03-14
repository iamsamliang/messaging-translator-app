import { fail, redirect } from '@sveltejs/kit';

export async function load({ cookies }) {
    const token: string | undefined = cookies.get("jwt");

    if (token === undefined) return;
    
    // grab the current user from backend using the cookie
    const response: Response = await fetch("http://localhost:8000/users/me/default", {
        method: "GET",
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) return;
    
    throw redirect(302, "/chat")
}

export const actions = {
    login: async ({ cookies, request }) => {
        const formData: FormData = await request.formData();

        try {
            const response: Response = await fetch("http://localhost:8000/login/access-token", {
                method: "POST",
                body: formData
            });

			if (!response.ok) {
				const errorResponse = await response.json();
                if (response.status === 401) return fail(401, {
                    incorrect: true
                })
				console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
				throw new Error(`Error code: ${response.status}`);
			}

			const resData = await response.json();

            const token = resData.access_token;
            
            // decode token to get expire date for cookie
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            const expireTimestamp = JSON.parse(jsonPayload).exp
            const expireDate: Date = new Date(expireTimestamp * 1000); // Convert to milliseconds (necessary)

            cookies.set('jwt', resData.access_token, { path: "/", expires: expireDate});

        } catch (error) {
            return fail(401, {
                error: error.message
            });
        }

        throw redirect(302, "/chat")
    }
}