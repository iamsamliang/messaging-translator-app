import { fromUnixTime } from 'date-fns';

export async function uploadImageToS3(url: string, presignedForm: FormData) {
    const response = await fetch(url, {
        method: 'POST',
        body: presignedForm
    });

    if (!response.ok) {
        // S3 returns error codes in XML
        const textResponse = await response.text();
        console.error('Server responded with an error:', textResponse);
        throw new Error(response.statusText);
    }
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

export async function refreshGETPresigned(key: string, IDs: number[]): Promise<Record<number, string>> {
    let sendData: number[] | number = IDs;

    if (key === "convo_id") sendData = IDs[0];

    const getURLResponse: Response = await fetch(
        `http://localhost:8000/aws/s3/generate-presigned-get`,
        {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [key]: sendData })
        }
    );

    if (!getURLResponse.ok) {
        const errorResponse = await getURLResponse.json();
        console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
        throw new Error(`Error code: ${getURLResponse.status}`);
    }

    return (await getURLResponse.json());
}