interface IconProps {
  name:
    | "camera"
    | "pie"
    | "counter"
    | "log"
    | "cpu"
    | "calendar"
    | "download"
    | "globe"
    | "dashboard"
    | "send"
    | "pause"
    | "play"
    | "dot";
  className?: string;
  size?: number;
}

export function Icon({ name, className = "", size = 16 }: IconProps) {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
  };
  switch (name) {
    case "camera":
      return (
        <svg {...props}>
          <rect x="3" y="6" width="18" height="13" rx="1.5" />
          <circle cx="12" cy="12.5" r="3.5" />
          <path d="M8 6l1.5-2h5L16 6" />
        </svg>
      );
    case "pie":
      return (
        <svg {...props}>
          <path d="M12 3v9h9a9 9 0 1 1-9-9z" />
          <path d="M12 3a9 9 0 0 1 9 9" />
        </svg>
      );
    case "counter":
      return (
        <svg {...props}>
          <rect x="3" y="5" width="18" height="14" rx="1.5" />
          <path d="M7 9v6M12 9v6M17 9v6" />
        </svg>
      );
    case "log":
      return (
        <svg {...props}>
          <path d="M5 4h11l3 3v13H5z" />
          <path d="M8 10h8M8 14h8M8 18h5" />
        </svg>
      );
    case "cpu":
      return (
        <svg {...props}>
          <rect x="6" y="6" width="12" height="12" rx="1" />
          <rect x="9" y="9" width="6" height="6" />
          <path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3" />
        </svg>
      );
    case "calendar":
      return (
        <svg {...props}>
          <rect x="3" y="5" width="18" height="16" rx="1.5" />
          <path d="M3 9h18M8 3v4M16 3v4" />
        </svg>
      );
    case "download":
      return (
        <svg {...props}>
          <path d="M12 4v12M7 11l5 5 5-5M4 20h16" />
        </svg>
      );
    case "globe":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
        </svg>
      );
    case "dashboard":
      return (
        <svg {...props}>
          <rect x="3" y="3" width="8" height="10" />
          <rect x="13" y="3" width="8" height="6" />
          <rect x="13" y="11" width="8" height="10" />
          <rect x="3" y="15" width="8" height="6" />
        </svg>
      );
    case "send":
      return (
        <svg {...props}>
          <path d="M4 12L20 4l-6 16-3-7z" />
        </svg>
      );
    case "pause":
      return (
        <svg {...props}>
          <rect x="7" y="5" width="3" height="14" />
          <rect x="14" y="5" width="3" height="14" />
        </svg>
      );
    case "play":
      return (
        <svg {...props}>
          <path d="M7 4l13 8-13 8z" />
        </svg>
      );
    case "dot":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" />
        </svg>
      );
  }
}
