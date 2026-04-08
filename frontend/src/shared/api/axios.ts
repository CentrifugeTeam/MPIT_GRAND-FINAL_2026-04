import axios from "axios";

export const api = axios.create({
  baseURL: "https://6641ce923d66a67b343500ea.mockapi.io",
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});
