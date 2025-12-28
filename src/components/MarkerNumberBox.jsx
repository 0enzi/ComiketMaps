const MarkerNumberBox = ({
  number,
  day,
  size = 32,
  fontSize = 16,
  style = {},
}) => {
  const isDay1 = day === "Day 1";

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: "white",
        border: "3px solid black",
        borderRadius: "4px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        fontWeight: "bold",
        fontSize: `${fontSize}px`,
        color: "black",
        flexShrink: 0,
        ...style,
      }}
    >
      {number}

      {/* Day indicator dot */}
      <div
        style={{
          position: "absolute",
          top: "-6px",
          right: "-6px",
          width: "16px",
          height: "16px",
          backgroundColor: isDay1 ? "#2196f3" : "#ff9800",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "2px solid white",
          boxShadow: "0 2px 4px rgba(0,0,0,0.3)",
        }}
      >
        <span
          style={{
            color: "white",
            fontSize: "10px",
            fontWeight: "bold",
          }}
        >
          {isDay1 ? "1" : "2"}
        </span>
      </div>
    </div>
  );
};

export default MarkerNumberBox;
