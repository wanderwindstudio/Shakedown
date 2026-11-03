Shader "Shakedown/Hull Surface"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct Input { float4 position : POSITION; float3 normal : NORMAL; half4 colour : COLOR; };
            struct Varying { float4 position : SV_POSITION; float3 world : TEXCOORD0; half3 normal : TEXCOORD1; half4 colour : COLOR; float fog : TEXCOORD2; };
            Varying Vert(Input v)
            {
                Varying o;
                o.world = TransformObjectToWorld(v.position.xyz);
                o.position = TransformWorldToHClip(o.world);
                o.normal = TransformObjectToWorldNormal(v.normal);
                o.colour = v.colour;
                o.fog = ComputeFogFactor(o.position.z);
                return o;
            }
            half4 Frag(Varying i) : SV_Target
            {
                Light light = GetMainLight(TransformWorldToShadowCoord(i.world));
                half3 normal = normalize(i.normal);
                half3 illumination = max(SampleSH(normal), half3(.12,.12,.12)) + light.color * saturate(dot(normal,light.direction)) * light.shadowAttenuation;
                return half4(MixFog(i.colour.rgb * illumination, i.fog), 1);
            }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On
            ColorMask 0
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            float4 Vert(float4 p : POSITION) : SV_POSITION { return TransformObjectToHClip(p.xyz); }
            half4 Frag() : SV_Target { return 0; }
            ENDHLSL
        }
    }
}
