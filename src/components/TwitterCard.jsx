const TwitterCard = ({ marker }) => {
  const formatDescription = (text) => {
    if (!text) return "";

    // Replace @mentions with links
    let formatted = text.replace(
      /@(\w+)/g,
      '<a href="https://twitter.com/$1" target="_blank" style="color: #1d9bf0; text-decoration: none;">@$1</a>'
    );

    // Replace URLs
    formatted = formatted.replace(
      /https?:\/\/\S+/g,
      (url) =>
        `<a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none;">${url}</a>`
    );

    // Convert newlines to breaks
    return formatted
      .split("\n")
      .map((line, i) => `<span key=${i}>${line}<br/></span>`)
      .join("");
  };

  return (
    <div
      style={{
        background: "#15202b",
        borderRadius: "12px",
        overflow: "hidden",
        border: "1px solid #38444d",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }}
    >
      {/* Banner */}
      {marker.banner && (
        <div
          style={{
            height: "125px",
            backgroundImage: `url(${marker.banner})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            position: "relative",
          }}
        >
          {/* Profile picture */}
          {marker.pfp && (
            <div
              style={{
                position: "absolute",
                bottom: "-40px",
                left: "16px",
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                border: "4px solid #15202b",
                overflow: "hidden",
                background: "#15202b",
              }}
            >
              <img
                src={marker.pfp}
                alt=""
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            </div>
          )}
        </div>
      )}

      <div
        style={{
          padding: "16px",
          paddingTop: marker.banner ? "50px" : "16px",
          color: "#e7e9ea",
        }}
      >
        {/* Name and handle */}
        <div style={{ marginBottom: "12px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
            }}
          >
            <div>
              <h3
                style={{
                  margin: 0,
                  fontSize: "18px",
                  fontWeight: "bold",
                  color: "#f7f9f9",
                  lineHeight: "1.3",
                }}
              >
                {marker.title}
              </h3>
              {marker.handle && (
                <div
                  style={{
                    fontSize: "14px",
                    color: "#8b98a5",
                    marginTop: "2px",
                  }}
                >
                  {marker.handle}
                </div>
              )}
            </div>

            {/* Twitter link button */}
            {marker.twitterUrl && (
              <a
                href={marker.twitterUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "#1d9bf0",
                  color: "white",
                  border: "none",
                  borderRadius: "9999px",
                  padding: "8px 16px",
                  fontSize: "14px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  textDecoration: "none",
                  transition: "background-color 0.2s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#1a8cd8")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "#1d9bf0")
                }
              >
                <svg
                  viewBox="0 0 24 24"
                  style={{ width: "18px", height: "18px", marginRight: "6px" }}
                >
                  <path
                    fill="currentColor"
                    d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
                  />
                </svg>
                Follow
              </a>
            )}
          </div>
        </div>

        {/* Description */}
        {marker.description && (
          <div
            style={{
              fontSize: "15px",
              lineHeight: "1.5",
              marginBottom: "16px",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word",
            }}
            dangerouslySetInnerHTML={{
              __html: formatDescription(marker.description),
            }}
          />
        )}

        {/* Booth info if exists */}
        {marker.booth && (
          <div
            style={{
              fontSize: "14px",
              color: "#8b98a5",
              padding: "8px 12px",
              backgroundColor: "rgba(29, 155, 240, 0.1)",
              borderRadius: "8px",
              marginBottom: "12px",
              border: "1px solid rgba(29, 155, 240, 0.2)",
            }}
          >
            Booth:{" "}
            <span style={{ color: "#e7e9ea", fontWeight: "500" }}>
              {marker.booth}
            </span>
          </div>
        )}

        {/* Day indicator */}
        <div
          style={{
            fontSize: "12px",
            color: "#8b98a5",
            padding: "6px 10px",
            backgroundColor:
              marker.day === "Day 1"
                ? "rgba(33, 150, 243, 0.1)"
                : "rgba(255, 152, 0, 0.1)",
            borderRadius: "6px",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            border: `1px solid ${
              marker.day === "Day 1"
                ? "rgba(33, 150, 243, 0.3)"
                : "rgba(255, 152, 0, 0.3)"
            }`,
          }}
        >
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: marker.day === "Day 1" ? "#2196f3" : "#ff9800",
            }}
          />
          {marker.day}
        </div>
      </div>
    </div>
  );
};

export default TwitterCard;
