import { useEffect, useState } from "react";

function CheckVisits() {
    const [visits, setVisits] = useState([]);
    const [userId, setUserId] = useState("");

    const fetchVisits = () => {
        let url = "/api/get_visits";
        if (userId) url += `?user_id=${userId}`;

        fetch(url, { credentials: "include" })
            .then((res) => {
                if (res.status === 403) {
                    alert("У вас недостаточно мощи");
                    return [];
                }
                return res.json();
            })
            .then((data) => setVisits(data))
            .catch((err) => console.error("Ошибка загрузки истории входов", err));
    };

    useEffect(() => {
        fetchVisits();
    }, []);

    return (
        <div>
            <h1>История заходов</h1>
            <input
                type="number"
                placeholder="ID пользователя"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
            />
            <button onClick={fetchVisits}>Фильтровать</button>

            <table border="1">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Логин</th>
                        <th>Время захода</th>
                    </tr>
                </thead>
                <tbody>
                    {visits.map((visit) => (
                        <tr key={visit.session_start}>
                            <td>{visit.user_id}</td>
                            <td>{visit.user_login}</td>
                            <td>{new Date(visit.session_start).toLocaleString()}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button onClick={() => navigate("/")}>⬅ Назад</button>
        </div>
    );
}

export default CheckVisits;
