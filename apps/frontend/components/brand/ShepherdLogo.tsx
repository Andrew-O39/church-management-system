import type { SVGProps } from "react";

/** Minimal geometric mark: flock + staff curve — flat, works at small sizes. */
export default function ShepherdLogo(props: SVGProps<SVGSVGElement>) {
  const { width = 36, height = 36, className, ...rest } = props;
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
      {...rest}
    >
      <circle cx="24" cy="24" r="22" fill="#4F46E5" />
      <path d="M16 26c0-4 3-7 8-7s8 3 8 7-3 7-8 7-8-3-8-7z" fill="white" />
      <circle cx="32" cy="24" r="3" fill="white" />
      <path
        d="M20 16c0-4 3-6 6-6s5 2 5 5-2 4-4 4"
        stroke="#F59E0B"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
