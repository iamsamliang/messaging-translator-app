import { verifyUserCaptcha } from "$lib/captcha.js";
import serverSettings from "$lib/config/config.server.js";
import { fail } from "@sveltejs/kit";
import { z } from "zod";

const forgotPWSchema = z.object({
    email: z.string({ required_error: "Email is required" }).toLowerCase().email({ message: "Invalid email address" }).min(1, { message: "Email cannot be empty" }).max(100, { message: "Email at most 100 characters" }),
    'g-recaptcha-response': z.string({ required_error: "Captcha is required"}).min(1, { message: "Captcha is required" })
});

export const actions = {
    sendEmail: async ( { request } ) => {
        const formData = await request.formData()
        const data = Object.fromEntries(formData);

        try {
            // form validation
            const parsedData = forgotPWSchema.parse(data);

            const recaptchaVerify = await verifyUserCaptcha(parsedData["g-recaptcha-response"], serverSettings.RECAPTCHA_SECRET_KEY);

            if (!recaptchaVerify.success) throw new Error(`Failed reCaptcha Verification`);

            const response: Response = await fetch(`${serverSettings.apiBaseURL}/users/forgot-password`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                if (response.status === 412) {
                    return fail(400, {
                        unverified: true
                    });
                }
                const errorData = await response.json();
                throw new Error(errorData.detail)
            }

            const successData = await response.json();

            return {
                message: successData.message
            }
        } catch (error) {
            if (error instanceof z.ZodError) {
                const { fieldErrors } = error.flatten();
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { 'g-recaptcha-response': gRecaptchaResponse, ...rest} = data;

                return fail(400, {
                    data: rest,
                    fieldErrors
                });
            } else if (error instanceof Error) {
                return fail(400, {
                    genErrors: error.message
                });
            }

            return fail(400, {
                genErrors: "An unknown error occurred",
            });
        }
    }
};