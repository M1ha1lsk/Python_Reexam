import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

function Register() {
  const [user_login, setLogin] = useState("");
  const [user_password, setPassword] = useState("");
  const [telegram_contact, setTelegram] = useState("");
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await axios.post(`${BASE_URL}/register/`, { user_login, user_password, telegram_contact });
      alert("✅ Регистрация успешна!");
      navigate("/login");
    } catch {
      alert("❌ Ошибка регистрации.");
    }
  };

  const handleYandexRegister = () => {
    window.location.href = `${BASE_URL}/auth/yandex`;
  };

  return (
    <div>
      <h1>Регистрация</h1>
      <input type="text" placeholder="Логин" onChange={(e) => setLogin(e.target.value)} />
      <input type="password" placeholder="Пароль" onChange={(e) => setPassword(e.target.value)} />
      <input type="text" placeholder="Telegram (только цифры)" onChange={(e) => setTelegram(e.target.value)} />
      <button onClick={handleRegister}>Зарегистрироваться</button>
      <button onClick={() => navigate("/")}>⬅ Назад</button>
      <button
        onClick={handleYandexRegister}
        style={{ marginTop: "20px" }}
      >
        Зарегистрироваться через Яндекс
      </button>
    </div>
  );
}

export default Register;
