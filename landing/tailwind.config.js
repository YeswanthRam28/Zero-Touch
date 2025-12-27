/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: "#5227FF",
                secondary: "#FF9FFC",
                accent: "#00F2FF",
                bg: "#030303",
                surface: "rgba(255, 255, 255, 0.05)",
                border: "rgba(255, 255, 255, 0.1)",
            },
            fontFamily: {
                heading: ['Outfit', 'sans-serif'],
                main: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
