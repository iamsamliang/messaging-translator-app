import type { UserCreate } from '$lib/interfaces/CreateModels.interface.js';
import { languages } from '$lib/languages.js';
import { fail, redirect } from '@sveltejs/kit';
import { z } from 'zod';
import serverSettings from '$lib/config/config.server.js';
import { verifyUserCaptcha } from '$lib/captcha.js';
import { rateLimiter } from '$lib/server/rate-limiter.js';

const createUserSchema = z.object({
    firstName: z.string({ required_error: "First name is required" }).trim().min(1, { message: "First name cannot be empty" }).max(100, { message: "First name at most 100 characters" }),
    lastName: z.string({ required_error: "Last name is required" }).trim().min(1, { message: "Last name cannot be empty" }).max(100, { message: "Last name at most 100 characters" }),
    language: z.enum(languages, { required_error: "You must select a language" }),
    password: z.string().min(1, { message: "Password cannot be empty" }).max(100, { message: "Password at most 100 characters" }),
    confPassword: z.string().min(1, { message: "Must confirm password" }).max(100, { message: "Password at most 100 characters" }),
    email: z.string({ required_error: "Email is required" }).toLowerCase().email({ message: "Invalid email address" }).min(1, { message: "Email cannot be empty" }).max(100, { message: "Email at most 100 characters" }),
    apiKey: z.string({ required_error: "An OpenAI API Key is required" }).trim().min(1, { message: "An OpenAI API Key is required" }).max(255, { message: "OpenAI API Key at most 255 characters" }),
    'g-recaptcha-response': z.string({ required_error: "Captcha is required"}).min(1, { message: "Captcha is required" })
}).superRefine(({ confPassword, password }, ctx) => {
    if ( confPassword !== password) {
        ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'Password and Confirm Password must match',
            path: ['password']
        });
        ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'Password and Confirm Password must match',
            path: ['confPassword']
        });
    }
})

export const actions = {
    create: async ({ cookies, request, getClientAddress }) => {
        const data = Object.fromEntries(await request.formData());

        try {
            const userSchema = createUserSchema.parse(data);

            const userIP = getClientAddress();
            const { success } = await rateLimiter.signupIP.limit(userIP);
            if (!success) throw new Error(`Too many signups. Please try again later.`);

            const recaptchaVerify = await verifyUserCaptcha(userSchema["g-recaptcha-response"], serverSettings.RECAPTCHA_SECRET_KEY);

            if (!recaptchaVerify.success) throw new Error(`Failed reCaptcha Verification`);

            const sendData: UserCreate = {
                first_name: userSchema.firstName,
                last_name: userSchema.lastName,
                email: userSchema.email,
                target_language: userSchema.language,
                password: userSchema.password,
                api_key: userSchema.apiKey,
            }

            console.log(`BACKEND_BASE_URL: ${serverSettings.apiBaseURL}`);

			const response: Response = await fetch(`${serverSettings.apiBaseURL}/users`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(sendData)
			});

			if (!response.ok) {
				const errorResponse = await response.json();
                throw new Error(errorResponse.detail)
			}

            const fetchReqData = await response.json();

            cookies.set('signupEmail', userSchema.email, { path: "/", maxAge: fetchReqData.cookie_expire_secs });
        } catch (error) {
            if (error instanceof z.ZodError) {
                const { fieldErrors } = error.flatten();
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { password, confPassword, 'g-recaptcha-response': gRecaptchaResponse, ...rest} = data;

                return fail(400, {
                    data: rest,
                    fieldErrors
                });
            } else if (error instanceof Error) {
                return fail(400, {
                    message: error.message
                });
            }

            // Handle other cases, defaulting to a generic message
            return fail(400, {
                message: "An unknown error occurred",
            });
        }

        redirect(303, '/signup/confirmation');
    }
}