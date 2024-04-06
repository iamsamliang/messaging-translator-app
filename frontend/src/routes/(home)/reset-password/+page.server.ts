import { verifyUserCaptcha } from '$lib/captcha.js';
import serverSettings from '$lib/config/config.server.js';
import { fail } from '@sveltejs/kit';
import { z } from 'zod'

const resetPasswordSchema = z.object({
    password: z.string().min(1, { message: "Password cannot be empty" }).max(100, { message: "Password at most 100 characters" }),
    confPassword: z.string().min(1, { message: "Must confirm password" }).max(100, { message: "Password at most 100 characters" }),
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

export function load({ url }) {
    const token = url.searchParams.get("token");

    return {
        token
    }
}

export const actions = {
    resetPassword: async ({ request }) => {
        const formData = await request.formData();
        const data = Object.fromEntries(formData);

        const { token, ...newData} = data;

        if (!token) {
            return fail(400, {
                genErrors: "Invalid Permissions."
            });
        }

        try {
            const parsedData = resetPasswordSchema.parse(newData);

            const recaptchaVerify = await verifyUserCaptcha(parsedData["g-recaptcha-response"], serverSettings.RECAPTCHA_SECRET_KEY);

            if (!recaptchaVerify.success) throw new Error(`Failed reCaptcha Verification`);

            const response = await fetch(`${serverSettings.apiBaseURL}/users/reset-password`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errorResponse = await response.json();
                throw new Error(errorResponse.detail);
            }
        } catch (error) {
            if (error instanceof z.ZodError) {
                const { fieldErrors } = error.flatten()
                return fail(400, {
                    fieldErrors
                });
            } else if (error instanceof Error) {
                return fail(400, {
                    genErrors: error.message
                });
            }

            return fail(400, {
                genErrors: "An unknown error occurred"
            })
        }
    }
}