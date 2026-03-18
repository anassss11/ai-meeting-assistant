import React from "react";

function ActionItems({ items }) {
  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Action Items</h2>
      {items.length > 0 ? (
        <ol style={listStyle}>
          {items.map((item, index) => (
            <li key={`${item.task}-${index}`} style={itemStyle}>
              <p style={taskStyle}><strong>Task:</strong> {item.task}</p>
              <p style={metaStyle}><strong>Owner:</strong> {item.owner}</p>
              <p style={metaStyle}><strong>Deadline:</strong> {item.deadline}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p style={emptyStyle}>No action items available yet.</p>
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
  marginBottom: "14px",
  lineHeight: 1.5,
};

const taskStyle = {
  margin: "0 0 4px",
};

const metaStyle = {
  margin: "0 0 2px",
  color: "#334155",
};

const emptyStyle = {
  margin: 0,
};

export default ActionItems;
