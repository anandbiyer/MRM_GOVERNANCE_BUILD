export interface NavItem {
  path: string;
  label: string;
  /** Hide the link unless the user's role has this permission (display only; the API enforces it). */
  permission?: string;
}

export const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Portfolio",
    items: [
      { path: "/", label: "Command Center" },
      { path: "/operations", label: "Operations Board" },  // Model 360 opens from any model row
      { path: "/monitoring", label: "Monitoring" },
      { path: "/data-audit", label: "Data Audit" },
    ],
  },
  {
    label: "Evidence & data",
    items: [
      { path: "/documents", label: "Document Centre" },
      { path: "/imports", label: "Import Centre" },
    ],
  },
  {
    label: "Control",
    items: [
      // No permission gate: any read role may view and download a report; only generating
      // needs report:generate, which the screen and the API both enforce (REQ-REG-10A).
      { path: "/reports/model-risk", label: "Model Risk Report" },
      { path: "/audit", label: "Audit Trail", permission: "audit:read" },
      { path: "/admin", label: "Admin" },
    ],
  },
];
