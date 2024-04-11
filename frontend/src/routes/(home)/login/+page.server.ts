import { fail, redirect } from '@sveltejs/kit';
import serverSettings from '$lib/config/config.server.js';
import { rateLimiter } from '$lib/server/rate-limiter.js';

export const actions = {
    login: async ({ request, getClientAddress, fetch }) => {
        const formData: FormData = await request.formData();

        try {
            // const inputEmail = formData.get("username")?.toString() as string;
            // const userIP = getClientAddress();
            // const { success: successIP } = await rateLimiter.loginIP.limit(userIP);
            // if (!successIP) throw new Error(`Attempted login too many times. Please try again later.`);
            // const { success: successEmail } = await rateLimiter.loginEmail.limit(inputEmail)
            // if (!successEmail) throw new Error(`Attempted login too many times. Please try again later.`);

            const response: Response = await fetch(`${serverSettings.apiBaseURL}/login/access-token`, {
                method: "POST",
                body: formData,
                credentials: 'include'
            });

			if (!response.ok) {
				const errorResponse = await response.json();

                if (response.status === 401) {
                    return fail(401, {
                        incorrect: true
                    });
                } else if (response.status === 412) {
                    return fail(401, {
                        unverified: true,
                    });
                }
                throw new Error(errorResponse.detail);
			}

			// const resData = await response.json();

            // const token = resData.access_token;
            
            // decode token to get expire date for setting cookie
            // const base64Url = token.split('.')[1];
            // const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            // const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            //     return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            // }).join(''));
            // const expireTimestamp = JSON.parse(jsonPayload).exp
            // const expireDate: Date = new Date(expireTimestamp * 1000); // Convert to milliseconds (necessary)

            // cookies.set('jwt', resData.access_token, { 
            //     path: "/",
            //     expires: expireDate,
            //     secure: true,
            //     httpOnly: true,
            //     sameSite: 'none',
            // });

        } catch (error) {
            if (error instanceof Error) {
                return fail(401, {
                    error: error.message
                });
            }

            // Handle other cases, defaulting to a generic message
            return fail(400, {
                error: "An unknown error occurred",
            });
        }

        redirect(303, "/chat");
    }
};