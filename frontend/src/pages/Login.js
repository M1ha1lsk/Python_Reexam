import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

function Login() {
  const [user_login, setLogin] = useState("");
  const [user_password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      await axios.post(
        `${BASE_URL}/login/`,
        { user_login, user_password },
        { withCredentials: true }
      );
      alert("✅ Вход успешен!");
      navigate("/");
    } catch {
      alert("❌ Неверные данные.");
    }
  };

  const handleYandexLogin = () => {
    window.location.href = `${BASE_URL}/auth/yandex`;
  };

  return (
    <div>
      <h1>Вход</h1>
      <input type="text" placeholder="Логин" onChange={(e) => setLogin(e.target.value)} />
      <input type="password" placeholder="Пароль" onChange={(e) => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Войти</button>
      <button onClick={() => navigate("/")}>⬅ Назад</button>

      <button
        onClick={handleYandexLogin}
        style={{
          marginTop: "20px",
          padding: "10px 15px",
          backgroundColor: "#ffcc00",
          border: "none",
          cursor: "pointer",
        }}
      >
        🔑 Войти через Яндекс
      </button>
    </div>
  );
}

export default Login;
