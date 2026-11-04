Shader "Shakedown/Spike/Sun glow"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        Pass
        {
            ZWrite Off
            Blend One One
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct Input { float4 position:POSITION; float2 uv:TEXCOORD0; };
            struct Varying { float4 position:SV_POSITION; float2 uv:TEXCOORD0; };
            Varying Vert(Input v) { Varying o; o.position=TransformObjectToHClip(v.position.xyz); o.uv=v.uv; return o; }
            half4 Frag(Varying i):SV_Target { half r=length(i.uv-.5)*2; half glow=pow(saturate(1-r),5)+step(r,.12); return half4(half3(1,.88,.66)*glow,1); }
            ENDHLSL
        }
    }
}
