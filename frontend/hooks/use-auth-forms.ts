"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/components/providers/auth-provider";
import { apiClient } from "@/lib/api/client";
import {
  loginSchema,
  registerSchema,
  type LoginValues,
  type RegisterValues,
} from "@/lib/schemas/auth";
import type { User } from "@/lib/types";

/**
 * Authentication form hooks.
 *
 * Each hook wires react-hook-form + Zod validation to a TanStack Query
 * mutation that consumes the backend auth endpoints. Feature pages consume
 * only these hooks and never touch the API client directly.
 */

export function useLogin() {
  const { login } = useAuth();
  const router = useRouter();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: ({ email, password }: LoginValues) =>
      login(email, password),
    onSuccess: () => router.replace("/dashboard"),
  });

  const onSubmit = form.handleSubmit((values) => mutation.mutate(values));
  return { form, mutation, onSubmit };
}

export function useRegister() {
  const router = useRouter();
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
      role: "logistics",
    },
  });

  const mutation = useMutation({
    mutationFn: async ({
      full_name,
      email,
      password,
      role,
    }: RegisterValues) => {
      await apiClient.post<User>("/auth/register", {
        full_name,
        email,
        password,
        role,
      });
    },
    onSuccess: () => router.replace("/login?registered=1"),
  });

  const onSubmit = form.handleSubmit((values) => mutation.mutate(values));
  return { form, mutation, onSubmit };
}

export function useLogout() {
  const { logout } = useAuth();
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      router.replace("/login");
      router.refresh();
    },
  });

  return { logout: useCallback(() => mutation.mutate(), [mutation]), mutation };
}
