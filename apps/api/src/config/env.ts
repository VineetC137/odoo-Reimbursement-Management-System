import dotenv from "dotenv";

dotenv.config();

export const env = {
  nodeEnv: process.env.NODE_ENV ?? "development",
  port: Number(process.env.PORT ?? 4000),
  databaseUrl: process.env.DATABASE_URL ?? "",
  clientUrl: process.env.CLIENT_URL ?? "http://localhost:5173",
  jwtAccessSecret: process.env.JWT_ACCESS_SECRET ?? "dev-access-secret",
  jwtRefreshSecret: process.env.JWT_REFRESH_SECRET ?? "dev-refresh-secret",
  restCountriesUrl:
    process.env.REST_COUNTRIES_URL ?? "https://restcountries.com/v3.1/all?fields=name,currencies,cca2",
  countryCacheMaxAgeHours: Number(process.env.COUNTRY_CACHE_MAX_AGE_HOURS ?? 24)
};
