import { stringify } from 'query-string';

const apiUrl = '/api';

export default {
    login: ({ username, password }) => {
        const request = new Request(`${apiUrl}/token`, {
            method: 'POST',
            body: stringify({
                username,
                password,
            }),
            headers: new Headers({ 'Content-Type': 'application/x-www-form-urlencoded' }),
        });
        return fetch(request)
            .then(response => {
                if (response.status < 200 || response.status >= 300) {
                    throw new Error(response.statusText);
                }
                return response.json();
            })
            .then(({ access_token }) => {
                localStorage.setItem('token', access_token);
            });
    },
    logout: () => {
        localStorage.removeItem('token');
        return Promise.resolve();
    },
    checkError: ({ status }) => {
        if (status === 401 || status === 403) {
            localStorage.removeItem('token');
            return Promise.reject();
        }
        return Promise.resolve();
    },
    checkAuth: () =>
        localStorage.getItem('token') ? Promise.resolve() : Promise.reject(),
    getPermissions: () => Promise.resolve(),
};