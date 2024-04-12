import { fromUnixTime } from 'date-fns';
import clientSettings from './config/config.client';

export async function uploadImageToS3(url: string, presignedForm: FormData) {
    const response = await fetch(url, {
        method: 'POST',
        body: presignedForm
    });

    if (!response.ok) throw new Error(`An error occured trying to upload your image. Please try again in a moment.`);
}

export function isPresignedExpired(url: string) {
    const urlParams = new URLSearchParams(new URL(url).search);

    // S3 Presigned URL Signature Version 4
    // const creationDate = parseISO(urlParams.get('X-Amz-Date'));
    // const expiresInSecs = Number(urlParams.get('X-Amz-Expires'));
    // const expiryDate = addSeconds(creationDate, expiresInSecs);

    // S3 Presigned URL Signature Version 2
    const expiryDate = fromUnixTime(Number(urlParams.get('Expires')));

    return expiryDate < new Date()
}

export async function refreshGETPresigned(key: string, IDs: number[], token: string): Promise<Record<number, string>> {
    let sendData: number[] | number = IDs;

    if (key === "convo_id") sendData = IDs[0];

    const getURLResponse: Response = await fetch(
        `${clientSettings.apiBaseURL}/aws/s3/generate-presigned-get`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ [key]: sendData })
        }
    );

    if (!getURLResponse.ok) throw new Error(`An error occured trying to load chat photos. Please refresh your page in a moment.`);

    return (await getURLResponse.json());
}