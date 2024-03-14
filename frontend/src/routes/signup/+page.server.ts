import type { UserCreate } from '$lib/interfaces/CreateModels.interface.js';
import { languages } from '$lib/languages.js';
import { fail, redirect } from '@sveltejs/kit';
import { z } from 'zod';

const createUserSchema = z.object({
    firstName: z.string({ required_error: "First name is required" }).trim().min(1, { message: "First name cannot be empty" }).max(100, { message: "First name at most 100 characters" }),
    lastName: z.string({ required_error: "Last name is required" }).trim().min(1, { message: "Last name cannot be empty" }).max(100, { message: "Last name at most 100 characters" }),
    language: z.enum(languages, { required_error: "You must select a language" }),
    password: z.string().min(1, { message: "Password cannot be empty" }).max(100, { message: "Password at most 100 characters" }),
    confPassword: z.string().min(1, { message: "Must confirm password" }).max(100, { message: "Password at most 100 characters" }),
    email: z.string({ required_error: "Email is required" }).email({ message: "Invalid email address" }).min(1, { message: "Email cannot be empty" }).max(100, { message: "Email at most 100 characters" }),
    apiKey: z.string({ required_error: "An OpenAI API Key is required" }).trim().min(1, { message: "An OpenAI API Key is required" }).max(255, { message: "OpenAI API Key at most 255 characters" }),
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
    create: async ({ request }) => {
        const data = Object.fromEntries(await request.formData());

        try {
            const userSchema = createUserSchema.parse(data);

            const sendData: UserCreate = {
                first_name: userSchema.firstName,
                last_name: userSchema.lastName,
                email: userSchema.email,
                target_language: userSchema.language,
                password: userSchema.password,
                api_key: userSchema.apiKey,
            }

			const response: Response = await fetch('http://localhost:8000/users', {
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

            throw redirect(302, '/login');
        } catch (error) {
            if (error instanceof z.ZodError) {
                const { fieldErrors } = error.flatten();
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { password, confPassword, ...rest} = data;

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
    }
}