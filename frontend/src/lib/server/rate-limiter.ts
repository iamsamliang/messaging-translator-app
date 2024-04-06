import { Redis } from '@upstash/redis'
import { Ratelimit } from "@upstash/ratelimit"; // for deno: see above
import serverSettings from '$lib/config/config.server';

const redis = new Redis({
  url: serverSettings.RATE_LIMITER_REDIS_URL,
  token: serverSettings.RATE_LIMITER_REDIS_TOKEN,
})

// Create ratelimiters
// Duration -> "ms" | "s" | "m" | "h" | "d"
export const rateLimiter = {
    loginEmail: new Ratelimit({
        redis,
        limiter: Ratelimit.fixedWindow(10, "2h"), // 10 attempts per 2 hours
        analytics: true,
        prefix: "ratelimit:loginEmail",
    }),
    loginIP: new Ratelimit({
        redis,
        limiter: Ratelimit.fixedWindow(50, "1d"), // 50 attempts per day
        analytics: true,
        prefix: "ratelimit:loginIP",
    }),
    signupIP: new Ratelimit({
        redis,
        limiter: Ratelimit.fixedWindow(100, "1d"), // 100 attempts per day
        analytics: true,
        prefix: "ratelimit:signupIP",
    })
};
