export function loadCaptcha(callbackFuncName: string): void {
		const script = document.createElement('script');
		script.src = `https://www.google.com/recaptcha/api.js?onload=${callbackFuncName}&render=explicit`;
		script.async = true;
		script.defer = true;
		document.head.appendChild(script);
}

export async function verifyUserCaptcha(captchaResponse: string, secretKey: string) {
    const recaptchaVerify: Response = await fetch(`https://www.google.com/recaptcha/api/siteverify`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `secret=${encodeURIComponent(secretKey)}&response=${encodeURIComponent(captchaResponse)}`
    });

    return (await recaptchaVerify.json());
}