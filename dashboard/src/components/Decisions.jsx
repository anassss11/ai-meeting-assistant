import React from "react";

function Decisions({ items }) {
  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Decisions</h2>
      {items.length > 0 ? (
        <ul style={listStyle}>
          {items.map((item) => (
            <li key={item} style={itemStyle}>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={emptyStyle}>No decisions available yet.</p>
      )}
    </section>
  );
}

const cardStyle = {
  padding: "20px",
  borderRadius: "18px",
  background: "rgba(255, 255, 255, 0.88)",
  boxShadow: "0 18px 45px rgba(15, 23, 42, 0.08)",
};

const titleStyle = {
  margin: "0 0 12px",
  fontSize: "22px",
};

const listStyle = {
  margin: 0,
  paddingLeft: "20px",
};

const itemStyle = {
  marginBottom: "8px",
  lineHeight: 1.5,
};

const emptyStyle = {
  margin: 0,
};

export default Decisions;