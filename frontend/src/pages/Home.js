import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

function Home() {
  const [authenticated, setAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get(`${BASE_URL}/api/get_user_role`, { withCredentials: true })
      .then((response) => {
        setUserRole(response.data.role);
      })
      .catch(() => {
        setUserRole(null);
      });

    // Проверяем активность сессии
    axios
      .get(`${BASE_URL}/check_session/`, { withCredentials: true })
      .then(() => {
        setAuthenticated(true);
      })
      .catch(() => {
        setAuthenticated(false);
      });
  }, []);

  const handleViewVisits = () => {
    if (userRole === "admin") {
      navigate("/check_visits");
    } else {
      alert("У вас недостаточно прав");
    }
  };

  return (
    <div>
      <h1>Добро пожаловать!</h1>
      {authenticated ? (
        <p>✅ Вы уже вошли в систему</p>
      ) : (
        <p>⚠️ Войдите или зарегистрируйтесь</p>
      )}

      {/* Кнопки регистрации и входа */}
      <button onClick={() => navigate("/register")}>📌 Регистрация</button>
      <button onClick={() => navigate("/login")}>🔑 Вход</button>
      <button onClick={() => window.location.reload()}>🔄 Проверить сессию</button>

      {/* Кнопка "Просмотр всех заходов" доступна только админам */}
      {userRole === "admin" && (
        <button onClick={handleViewVisits}>👀 Просмотр всех заходов</button>
      )}
    </div>
  );
}

export default Home;
