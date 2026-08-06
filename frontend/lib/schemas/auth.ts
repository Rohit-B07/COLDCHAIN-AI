import { z } from "zod";

import type { UserRole } from "@/lib/types";

/**
 * Zod schemas for authentication forms.
 *
 * Validation mirrors the backend DTOs (`LoginRequest`, `RegisterRequest`) so
 * the client rejects invalid input before any network request is made.
 */

export const loginSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginValues = z.infer<typeof loginSchema>;

/** Roles a self-registering user may request. */
export const registerableRoles: readonly UserRole[] = [
  "logistics",
  "dispatcher",
  "driver",
] as const;

export const registerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(1, "Full name is required")
      .max(255, "Full name must be at most 255 characters"),
    email: z
      .string()
      .trim()
      .min(1, "Email is required")
      .email("Enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(128, "Password must be at most 128 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    role: z.enum(registerableRoles, {
      message: "Please select a valid role",
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type RegisterValues = z.infer<typeof registerSchema>;
